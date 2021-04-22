# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _compute_immediatly_usable_qty(self):
        for move in self:
            usable_qty = move.with_context(
                location=move.location_id.id
            ).product_id.immediately_usable_qty

            zone = move.raw_material_production_id.availability_zone_id
            if zone:
                usable_qty_zone = move.with_context(
                    location=zone.id
                ).product_id.immediately_usable_qty
            else:
                usable_qty_zone = usable_qty
            move.qty_immediatly_usable = usable_qty
            move.qty_immediatly_usable_mrp_zone = usable_qty_zone

    # For now, the 2 next fields are only displayed in mrp.production view
    # If we start to display it eslewhere, the string won't mean anything, we
    # will have to change them then.
    qty_immediatly_usable = fields.Float(
        compute="_compute_immediatly_usable_qty",
        string="Qty Immedialty Usable in Production",
    )
    qty_immediatly_usable_mrp_zone = fields.Float(
        compute="_compute_immediatly_usable_qty_zone", string="Qty Usable in Total"
    )

    # Call by cron to replace mrp cron, as it is too slow to check procurement
    # state and move assignement and we need to do it more than once per day
    def check_move_avaibility_mrp(self):
        # since we check the product stock in each job, better to group
        # move by product to avoid doing it multiple times
        # for performance issues with the needed sorting, we let's do it with sql query
        self.env.cr.execute(
            """
            SELECT m.id FROM stock_move m
            JOIN mrp_production mo ON mo.id = m.raw_material_production_id
            WHERE m.state = 'confirmed'
            ORDER BY m.product_id,mo.expedition_date,mo.priority desc
        """
        )
        move_ids = [x[0] for x in self.env.cr.fetchall()]

        for x in range(0, len(move_ids), 200):
            self.browse(
                move_ids[x : x + 200]
            ).with_delay().check_mrp_raw_material_availability()

    def check_mrp_raw_material_availability(self):
        # We want to know if raw materials are available in a zone which can be
        # different than the MO src_location. In that case it is the
        # reservation_zone_id which is considered (it has to be a parent of
        # src_location)

        # since we want to check availability in parent location, reserving quant the
        # normal way is kind of counter productive. We have to reserve quant normally,
        # and then add a logic to force assign depending on the parent location, which
        # contain most of the stock...
        # It is actually kind of useless to reserve quant in producion location
        # instead of just forcing availibility for all
        # it will avoid quant exchange on transfer, etc...
        # moves.action_assign()

        # If there is not enought stock check in reservation_zone_id and force assign
        # if zone Has enought stock. (only for raw material moves)
        # We want the OF to be awaiting raw materials only if there is no stock in the
        # building...
        # waiting_moves = moves.filtered(
        # lambda m: m.state != "assigned" and m.raw_material_production_id
        # )

        # Recheck states of moves. Because between the job creation and the job
        # start date, it is possible that a stock move has been done or cancel...
        # This job may then change the done/cancel move state to assign, which
        # is definitly not wanted!
        moves = self.filtered(lambda m: m.state == "confirmed")
        loc_prod = {}

        for move in moves:
            location = (
                move.raw_material_production_id.availability_zone_id or move.location_id
            )
            if location not in loc_prod:
                loc_prod[location] = self.env["product.product"]
            if move.product_id not in loc_prod[location]:
                loc_prod[location] |= move.product_id
        qty_available_reservation = {}
        for location in loc_prod.keys():
            prod_qties_reserved = (
                loc_prod[location]
                .with_context(location=location.id)
                ._get_product_mrp_reserved()
            )
            prod_qties = (
                loc_prod[location]
                .with_context(location=location.id)
                ._product_available()
            )

            qty_available_reservation[location] = {
                id: prod_qties[id]["qty_available"] - prod_qties_reserved[id]
                for id in prod_qties_reserved.keys()
            }
        first_time_out_of_stock_mo = self.env["mrp.production"]
        to_force_assign = self.env["stock.move"]
        for move in self:
            mo = move.raw_material_production_id
            location = mo.availability_zone_id or move.location_id
            qty_available = qty_available_reservation.get(location, {}).get(
                move.product_id.id, 0.0
            )
            if move.product_uom_qty <= qty_available:
                to_force_assign |= move
                qty_available_reservation[location][
                    move.product_id.id
                ] -= move.product_uom_qty
            # If the move is not reserved, it means there is a shortage, at least on
            # in the zone (normaly the warehouse)
            else:
                if not mo.had_shortage:
                    first_time_out_of_stock_mo |= mo

        if to_force_assign:
            # it is not really a reservation, we don't want to manage stock move line
            # because we may want to reserve in a parent location. Also this is not
            # the stock that will really be consumed, it will be reordered
            to_force_assign.write({"state": "assigned"})
        first_time_out_of_stock_mo.write({"had_shortage": True})
        available_mo = to_force_assign.mapped("raw_material_production_id").filtered(
            lambda mo: mo.had_shortage and mo.reservation_state == "assigned"
        )
        available_mo.write({"available_date": fields.Date.today()})
