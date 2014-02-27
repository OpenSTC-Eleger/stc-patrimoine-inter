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

{
    "name": "openstc_patrimoine_inter",
    "version": "0.1",
    "depends": ["openstc_patrimoine","openstc"],
    "author": "BP",
    "category": "Category",
    "description": """
    Sub-module of OpenSTC-Patrimoine to link patrimony with OpenSTC Module : 
    * Generate intervention for each contract
    * Generate n tasks for each contract (using recurrence to simplify creation)
    
    """,
    "data": [
            "views/openstc_patrimoine_view.xml",
            "views/openstc_patrimoine_menu.xml",
            
            "security/ir.model.access.csv",
             ],
    "demo": [],
    "test": [],
    "installable": True,
    "active": False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
