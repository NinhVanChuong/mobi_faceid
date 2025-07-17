# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import ldap
import logging
from ldap.filter import filter_format

from odoo import _, api, fields, models, tools
from odoo.exceptions import AccessDenied
from odoo.tools.misc import str2bool
from odoo.tools.pycompat import to_text

_logger = logging.getLogger(__name__)


class CompanyLDAP(models.Model):
    _inherit = "res.company.ldap"

    def _authenticate(self, conf, login, password):
        """
        Authenticate a user against the specified LDAP server.

        In order to prevent an unintended 'unauthenticated authentication',
        which is an anonymous bind with a valid dn and a blank password,
        check for empty passwords explicitely (:rfc:`4513#section-6.3.1`)
        :param dict conf: LDAP configuration
        :param login: username
        :param password: Password for the LDAP user
        :return: LDAP entry of authenticated user or False
        :rtype: dictionary of attributes
        """

        if not password:
            return False
        login += "@mobifone.vn"
        dn, entry = self._get_entry(conf, login)
        if not dn:
            return False
        try:
            conn = self._connect(conf)
            conn.simple_bind_s(dn, to_text(password))
            conn.unbind()
        except ldap.INVALID_CREDENTIALS:
            return False
        except ldap.LDAPError as e:
            _logger.error('An LDAP exception occurred: %s', e)
            return False
        return entry