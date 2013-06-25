PyIssues
========
A simple issue tracker that stores its data in a folder which can be
version controlled.

Similar in concept to git-issues but you are left
responsible for commiting the issuess data.  Should just require a
`git add issues` when you modify any issues before you commit.

Status
------
I'm still playing with this so the data structure may change.
You have been warned!

Installation
------------
::

    pip install https://github.com/tf198/pyissues/tarball/master

Usage
-----

::

    $ pyissues create
    >  Description []: My test issue
    >  Status [open]: 
    >  Assigned [no-one]: 
    >  Priority [medium]: low
    >  Version [0.1]: 
    >  Milestone [0.1]: 
    >  Issue - Ctrl D to exit..
    > This is a test
    > <Ctrl^D>

    $ pyissues list
    > UUID   Description                    Owner    Assigned Priority Created   
    > ---------------------------------------------------------------------------
    > cf6edb My test issue                  tris     no-one   low      2013-06-07
    > 42631a Test issue                     tris     no-one   medium   2013-06-07

    $ pyissues list --priority low
    > UUID   Description                    Owner    Assigned Priority Created   
    > ---------------------------------------------------------------------------
    > cf6edb My test issue                  tris     no-one   low      2013-06-07

    $ pyissues show cf6e
    > UUID           : cf6edbd7-68c9-402d-b407-33c641ee6208
    > description    : My test issue
    >
    > owner   : tris                    assigned  : no-one              
    > version : 0.1                     milestone : 0.1                 
    > created : 2013-06-07 00:28:37     updated   : 2013-06-07 00:28:58 
    > ... some more info

    $ pyissues update cf6e assigned tris
    $ pyissues close cf6e -m "I fixed this"


