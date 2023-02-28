
class TestHelper():
    """ Allow to populate data """

    def create_or_update(self, model, xmlid, values, module="any"):
        """Create or update a record matching xmlid with values
        Code from Anthem lib
        """
        if isinstance(model, str):
            model = self.env[model]
        xmlid = "%s.%s" % (module.lower(), xmlid.lower())
        record = self.env.ref(xmlid, raise_if_not_found=False)
        if record:
            record.update(values)
        else:
            record = model.create(values)
            self.add_xmlid(record, xmlid)
        return record

    def add_xmlid(self, record, xmlid, noupdate=False):
        """Add a XMLID on an existing record
        Code from Anthem lib
        """
        ir_model_data = self.env["ir.model.data"]
        try:
            if hasattr(ir_model_data, "xmlid_lookup"):
                # Odoo version <= 14.0
                ref_id, __, __ = ir_model_data.xmlid_lookup(xmlid)
            else:
                # Odoo version >= 15.0
                ref_id, __, __ = ir_model_data._xmlid_lookup(xmlid)
        except ValueError:
            pass  # does not exist, we'll create a new one
        else:
            return ir_model_data.browse(ref_id)
        if "." in xmlid:
            module, name = xmlid.split(".")
        else:
            module = ""
            name = xmlid
        return self.env["ir.model.data"].create(
            {
                "name": name,
                "module": module,
                "model": record._name,
                "res_id": record.id,
                "noupdate": noupdate,
            }
        )
