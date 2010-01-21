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
import lxml
from distutils.core import setup
try:
    import py2exe
except ImportError:
    pass
# To get around py2exe strangeness
import sys; sys.path.append("mapcreator")


setup(name = 'mapcreator',
      version='0.1',      
      description = 'mapcreator tool',
      author = 'Nokia sysdoc tools team',
      license='EPL',
      packages=['mapcreator'],
      console=['mapcreator/mapcreator.py'],
      options={"py2exe":
                    {'packages':['lxml', 'gzip']}
               }
)
