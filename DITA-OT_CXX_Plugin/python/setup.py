# Copyright (c) 2007-2010 Nokia Corporation and/or its subsidiary(-ies) All rights reserved.
# This component and the accompanying materials are made available under the terms of the License 
# "Eclipse Public License v1.0" which accompanies this distribution, 
# and is available at the URL "http://www.eclipse.org/legal/epl-v10.html".
#
# Initial Contributors:
# Nokia Corporation - initial contribution.
#
# Contributors:
# System Documentation Tools
# Description:
#
from distutils.core import setup
try:
    import py2exe
except ImportError:
    pass

setup(name = 'DITA OT Support',
      version='0.1.1',      
      description = 'Support for the DITA Open Toolkit',
      author = 'Nokia sysdoc tools team',
      license='EPL',
      console=[
               'mpdot.py',
               'linkcheck.py',
               ],
      options={"py2exe":
                    {'packages':['xml.etree', 'gzip']}
               }
)
