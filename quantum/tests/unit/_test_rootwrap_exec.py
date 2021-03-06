# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2012 OpenStack, LLC
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os

import fixtures

from quantum.agent.linux import utils
from quantum.openstack.common import log as logging
from quantum.tests import base


LOG = logging.getLogger(__name__)


class RootwrapTestExec(base.BaseTestCase):
    """Simple unit test to test the basic rootwrap mechanism

    Essentially hello-world.  Just run a command as root and check that
    it actually *did* run as root, and generated the right output.

    NB that this is named _test_rootwrap so as not to get run by default
    from scripts like tox.  That's because it actually executes a sudo'ed
    command, and that won't work in the automated test environment, at
    least as it stands today.  To run this, rename it to
    test_rootwrap.py, or run it by hand.
    """

    def setUp(self):
        super(RootwrapTestExec, self).setUp()
        self.cwd = os.getcwd() + "/../../.."
        # stuff a stupid bash script into /tmp, so that the next
        # method can execute it.
        self.test_file = self.useFixture(
            fixtures.TempDir()).join("rootwrap-test.sh")
        with open(self.test_file, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write('ID=`id | sed \'s/uid=//\' | sed \'s/(.*//\' `\n')
            f.write("echo $ID $1\
\" Now is the time for all good men to come \
to the aid of their party.\"\n")
        # we need a temporary conf file, pointing into pwd for the filter
        # specs. there's probably a better way to do this, but I couldn't
        # figure it out.  08/15/12 -- jrd
        self.conf_file = self.useFixture(
            fixtures.TempDir()).join("rootwrap.conf")
        with open(self.conf_file, 'w') as f:
            f.write("# temporary conf file for rootwrap-test, " +
                    "generated by test_rootwrap.py\n")
            f.write("[DEFAULT]\n")
            f.write("filters_path=" + self.cwd +
                    "/quantum/tests/etc/rootwrap.d/")
        # now set the root helper to sudo our rootwrap script,
        #  with the new conf
        self.root_helper = "sudo " + self.cwd + "/bin/quantum-rootwrap "
        self.root_helper += self.conf_file

    def runTest(self):
        try:
            result = utils.execute(["bash", self.test_file, 'arg'],
                                   self.root_helper)
            self.assertEqual(result,
                             "0 arg Now is the time for all good men to \
come to the aid of their party.")
        except Exception, ex:
            LOG.exception("Losing in rootwrap test")

    def tearDown(self):
        os.remove(self.test_file)
        os.remove(self.conf_file)
        super(RootwrapTestExec, self).tearDown()
