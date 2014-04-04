# -*- coding: utf-8 -*-

##############################################################################
#    Copyright (C) 2012 SICLIC http://siclic.fr
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
#############################################################################
from openbase.openbase_core import OpenbaseCore
from osv import fields, osv
import netsvc

class intervention(OpenbaseCore):
    _inherit = 'project.project'
    
    """ Before cancelling interventions, cancel their linked contracts"""
    def action_cancelled(self, cr, uid, ids):
        wkf_service = netsvc.LocalService('workflow')
        for inter in self.browse(cr, uid, ids):
            if inter.contract_id.state != 'cancel':
                inter.contract_id.write({'cancel_reason':inter.cancel_reason})
                wkf_service.trg_validate(uid, 'openstc.patrimoine.contract', inter.contract_id.id, 'cancel', cr)
        return super(intervention, self).action_cancelled(cr, uid, ids)
    
    _columns = {
        'contract_id': fields.many2one('openstc.patrimoine.contract', 'Contract', ondelete="cascade"),
        }
intervention()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: