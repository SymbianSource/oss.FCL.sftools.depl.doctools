
#include "xmlditaparammap.h"
#include <stdio.h>

void DumpDocBlockContents(const DocBlockContentsType& theBlock)
{
	ParamDescriptionMap::ConstIterator it;
	printf("DumpDocBlockContents:\n");
	printf("Parameters:\n");
	for (it = theBlock.paramMap.begin(); it != theBlock.paramMap.end(); ++it) {
		printf("%s: %s\n", it.key().data(), it.data().data());
	}
	printf("Template types:\n");
	for (it = theBlock.tparamMap.begin(); it != theBlock.tparamMap.end(); ++it) {
		printf("%s: %s\n", it.key().data(), it.data().data());
	}
	printf("Return: %s\n", theBlock.returnDoc.data());
	printf("\n");
}

