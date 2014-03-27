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
               'recurrence_ids':[(4,line.id) for line in contract.contract_line]
               }
        return ret
    
    """ @note: Generate intervention and link it with recurrent tasks"""
    def generate_intervention(self, cr, uid, ids, context=None):
        for contract in self.browse(cr, uid, ids, context=context):
            vals = self.prepare_intervention(cr, uid, contract, context=context)
            ret = self.pool.get('project.project').create(cr, uid, vals, context=context)
            contract.write({'intervention_id':ret})
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
            recurrence_values.append((4,recurrence_obj.copy(cr, uid, recurrence.id, {'occurrence_ids':[(5,)]}, context=context)))
        ret.update({
            'intervention_id':False,
            'contract_line':recurrence_values
            })
        return ret
        
openstc_patrimoine_contract()


class openstc_patrimoine_contrat_line(OpenbaseCore):
    _inherit = 'openbase.recurrence'
    _name = 'openstc.task.recurrence'
    
     
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

    
    #get first occurrence in draft state as next_inter, and last occurrence in done state as last_inter
    def _get_next_inter(self, cr, uid, ids, name, args, context=None):
        ret = {}
        for line in self.browse(cr, uid, ids, context=context):
            next_inter = False
            last_inter = False
            ret[line.id] = {}
            #get occurrences list, ordered by date_order (according to _order attribute of object)
            for occurrence in line.occurrence_line:
                if occurrence.is_active() and not next_inter:
                    next_inter = occurrence.date_order
                elif not occurrence.is_active() and not last_inter:
                    last_inter = occurrence.date_order
            ret[line.id] = {'next_inter':next_inter, 'last_inter':last_inter}
        return ret
    
    _columns = {
        'name':fields.char('Name',size=128, required=True),
        'contract_id':fields.many2one('openstc.patrimoine.contract', 'Contract linked'),
        'is_team':fields.boolean('Is Team Work'),
        'agent_id':fields.many2one('res.users', 'Agent'),
        'team_id':fields.many2one('openstc.team', 'Team'),
        'task_categ_id':fields.many2one('openstc.task.category', 'Task category'),
        'planned_hours':fields.float('Planned hours'),
        'supplier_cost':fields.float('Supplier Cost'),
        
        'last_inter':fields.function(_get_next_inter, multi='recur', method=True, type='date',string='Date last intervention', help="Planned date of the next intervention, you can change it as you want.",
                                     store={'openstc.patrimoine.contract.occurrence':(_get_line_from_occur, ['date_order','state'], 10),
                                            'openstc.task.recurrence':(lambda self,cr,uid,ids,ctx={}:ids,['occurence_line'],11)}),
        'next_inter':fields.function(_get_next_inter, multi='recur', method=True, type='date', string='Date next intervention', help="Date of the last intervention executed in this contract",
                                     store={'openstc.patrimoine.contract.occurrence':(_get_line_from_occur, ['date_order','state'], 10),
                                            'openstc.task.recurrence':(lambda self,cr,uid,ids,ctx={}:ids,['occurence_line'],11)}),
        
        'date_start':fields.related('contract_id', 'date_start_order', type="datetime", required=False, string="Date start", store=store_related),
        'date_end':fields.related('contract_id', 'date_end_order', type="datetime", required=False, string="Date end", store=store_related),
        'internal_inter':fields.related('contract_id','internal_inter',type='boolean', string='Internal Intervention', store=store_related),
        'technical_service_id':fields.related('contract_id','technical_service_id',type='many2one',relation='openstc.service', string='Internal Service', store=store_related),
        
        'equipment_id':fields.related('contract_id','equipment_id',type='many2one',relation='openstc.equipment',string="equipment", store=store_related),
        'site_id':fields.related('contract_id','site_id',type='many2one',relation='openstc.site',string="Site", store=store_related),
        'patrimoine_is_equipment':fields.related('contract_id','patrimoine_is_equipment',type='boolean',string='Is Equipment',store=store_related),
        
        'patrimoine_name':fields.related('contract_id','patrimoine_name',type='char', string="patrimony", store=store_related),
        
        'recurrence':fields.boolean('has recurrence'),
        'occurrence_ids':fields.one2many('project.task','recurrence_id', 'Tasks'),
        'intervention_id':fields.many2one('project.project', 'Intervention'),
        }
    _defaults = {
        'recur_length_type':lambda *a:'until',
        'recurrence': lambda *a: False,
        'recur_month_type':'monthday',
        'is_team': lambda *a: False
        }
    
    _order = "next_inter,technical_service_id"
    
    """
    @param record: browse_record object of contract.line to generate tasks
    @param date: datetime object representing date_start of the task to be created after this method
    @return: data used to create tasks
    @note: this method override the one created in openbase.recurrence to customize behavior"""
    def prepare_occurrences(self, cr, uid, record, date, context=None):
        
        val = super(openstc_patrimoine_contrat_line, self).prepare_occurrences(cr, uid, record, date, context=context)
        #assert record.contract_id.intervention_id, 'Error: intervention_id (project.project) is not present on contract %s :%s' % (str(record.contract_id.id),record.contract_id.name)
        return {
            'name':record.name,
            'recurrence_id':val.get('recurrence_id'),
            'date_deadline':val.get('date_start'),
            #'project_id':record.contract_id.intervention_id.id,
            'user_id':record.agent_id.id if not record.is_team else False,
            'team_id':record.team_id.id if record.is_team else False,
            'planned_hours': record.planned_hours
            
            }
    
openstc_patrimoine_contrat_line()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: