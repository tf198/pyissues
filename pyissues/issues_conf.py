# Options for fields
status = ('open', 'closed', 'archived')
priority = ('low', 'medium', 'high', 'blocker')
milestone = ('0.1', '0.2', '0.3')
version = ('0.1', '0.2', '0.3')

# Be careful editing anything beyond this point!
import getpass

_fields = (('description',  ''),
           ('status',       'open'),
           ('owner',        getpass.getuser()),
           ('assigned',     'no-one'),
           ('priority',     'medium'),
           ('version',      version[0]),
           ('milestone',    milestone[0]),
           ('created',      None), # autoset
           ('updated',      None), # autoset
           ('body',         ''),
           ('comments',     []),
           ('attachments',  []),
           ('uuid',         None))

_required = ('description', 'status', 'assigned', 'priority', 'version', 'milestone')

_index = ('description', 'status', 'owner', 'assigned', 'priority', 'version', 'milestone', 'created')

_default_filters = {'status': 'open'}

_template = '''
UUID           : {uuid}
description    : {description}

owner   : {owner:20s}    assigned  : {assigned:20s}
version : {version:20s}    milestone : {milestone:20s}
created : {created:20s}    updated   : {updated:20s}

Issue
=====
{body}

Comments
========
{comments}

Attachments
===========
{attachments}
'''