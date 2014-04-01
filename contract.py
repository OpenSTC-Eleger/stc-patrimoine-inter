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

class openstc_patrimoine_contract(OpenbaseCore):
    _inherit = 'openstc.patrimoine.contract'
    
    _fields_names = {
        'contract_line_names': 'contract_line'
        } 
    
    _actions = {
        'create_inter':lambda self,cr,uid,record,groups_code: record.state in ('draft',),
        }
    
    _columns = {
        'intervention_id':fields.many2one('project.project'),
        'contract_line':fields.one2many('openstc.task.recurrence', 'contract_id', 'Intervention Lines'),
        }
    
    def get_all_recurrences(self, cr, uid, ids, context=None):
        line_obj = self.pool.get("openstc.task.recurrence")
        for contract in self.browse(cr, uid, ids, context=context):
            line_ids = [line.id for line in contract.contract_line if line.recurrence]
            line_obj.generate_dates(cr, uid, line_ids, context=context)
        return True
    
    """ @note: Override of Wkf method, generate tasks according to recurrence setting"""
    def wkf_wait(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'wait'},context=context)
        self.get_all_recurrences(cr, uid, ids, context=context)
        return True
    
    """ @return: dict containing values used to create intervention"""
    def prepare_intervention(self, cr, uid, contract ,context=None):
        ret = {'name':contract.name,
               'description':contract.description,
               'service_id':contract.technical_service_id.id if contract.internal_inter and contract.technical_service_id else False,
               'has_equipment':contract.patrimoine_is_equipment,
               'equipment_id':contract.equipment_id.id if contract.patrimoine_is_equipment and contract.equipment_id else False,
               'site1':contract.site_id.id if not contract.patrimoine_is_equipment and contract.site_id else False,
               'date_deadline':contract.date_end_order,
               'recurrence_ids':[(4,line.id) for line in contract.contract_line],
               'contract_id':contract.id,
               }
        return ret
    
    """ @note: Generate intervention and link it with recurrent tasks"""
    def generate_intervention(self, cr, uid, ids, context=None):
        inter_obj = self.pool.get('project.project')
        task_obj = self.pool.get('project.task')
        for contract in self.browse(cr, uid, ids, context=context):
            #create and link intervention according to the contract data
            vals = self.prepare_intervention(cr, uid, contract, context=context)
            ret = self.pool.get('project.project').create(cr, uid, vals, context=context)
            contract.write({'intervention_id':ret})
            #retrieve all tasks of the contract and link them with the newly created intervention
            task_ids = task_obj.search(cr, uid, [('recurrence_id.contract_id.id','=',contract.id)], context=context)
            if task_ids:
                inter_obj.write(cr, uid, [ret], {'tasks':[(4,task_id) for task_id in task_ids]})
        return True
    
    """ @note: Override of Wkf method, generate intervention and update state"""
    def wkf_confirm(self, cr, uid, ids, context=None):
        super(openstc_patrimoine_contract, self).wkf_confirm(cr, uid, ids, context=context)
        self.generate_intervention(cr, uid, ids, context=context)
        return True
    
    """ @return: dict with updated values from the parent method, remove all occurrences for the new contract, keep only recurrences setting"""
    def prepare_default_values_renewed_contract(self, cr, uid, contract, context=None):
        ret = super(openstc_patrimoine_contract, self).prepare_default_values_renewed_contract(cr, uid, contract, context=context)
        recurrence_obj = self.pool.get('openstc.task.recurrence')
        recurrence_values = []
        for recurrence in contract.contract_line:
            recurrence_values.append((4,recurrence_obj.copy(cr, uid, recurrence.id, {'occurrence_ids':[(5,)], 'intervention_id':False}, context=context)))
        ret.update({
            'intervention_id':False,
            'contract_line':recurrence_values
            })
        return ret
        
openstc_patrimoine_contract()


class openstc_task_recurrence(OpenbaseCore):
    _inherit = 'openstc.task.recurrence'
    
     
    def _get_line_from_occur(self, cr, uid, ids, context=None):
        occ = self.pool.get("openstc.patrimoine.contract.occurrence").browse(cr, uid, ids, context=context)
        ret = []
        for item in occ:
            if item.contract_line_id.id not in ret:
                ret.append(item.contract_line_id.id)
        return ret
    
    def _get_line_from_contracts(self, cr, uid, ids, context=None):
        ret = []
        for contract in self.browse(cr, uid, ids, context=None):
            ret.extend([line.id for line in contract.contract_line])
        return ret
    
    store_related = {'openstc.patrimoine.contract':[_get_line_from_contracts,['equipment_id','site_id','patrimoine_is_equipment'],10],
                    'openstc.task.recurrence':[lambda self,cr,uid,ids,ctx={}:ids,['contract_id'],9]}

    

    
    """ Instead of using related field, i use functionnal field (because patrimoine module will need this behavior too
    @return: values of 'related' values of fields defined in 'name' params"""
    def related_fields_function(self, cr, uid, ids, name, args, context=None):
        ret = super(openstc_task_recurrence, self).related_fields_function(cr, uid, ids, name, args, context=None)
        for recurrence in self.browse(cr, uid, ids, context=context):
            contract = recurrence.contract_id 
            if not recurrence.from_inter and contract:
                val = {
                    'internal_inter':contract.internal_inter,
                    'technical_service_id':contract.technical_service_id.id if contract.technical_service_id else False,
                    'patrimoine_is_equipment':contract.patrimoine_is_equipment,
                    'site_id':contract.site_id.id if contract.site_id else False,
                    'equipment_id':contract.equipment_id.id if contract.equipment_id else False,
                    'patrimoine_name':contract.patrimoine_name,
                    'date_start':contract.date_start_order,
                    'date_end':contract.date_end_order
                    }
                ret[recurrence.id].update(val)
        return ret
    
    _columns = {
        
        'contract_id':fields.many2one('openstc.patrimoine.contract', 'Contract linked'),
        }
    
    def create(self, cr, uid, vals, context=None):
        #retrieve value of 'from_inter' according to 'contract_id' value
        if vals.get('contract_id',False):
            vals.update({'from_inter':False})
        ret = super(openstc_task_recurrence, self).create(cr, uid, vals, context=context)
        return ret
    
openstc_task_recurrence()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: