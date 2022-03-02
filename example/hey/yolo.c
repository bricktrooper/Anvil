#include <stdio.h>

#include "test/yolo.h"

char const * YOLO_1 = "YOLO_1";

void message(char const * caller, char const * file)
{
	printf("Calling '%s()' from '%s'\r\n", caller, file);
}
