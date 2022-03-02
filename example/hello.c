#include <stdio.h>

#include "hello.h"
#include "test/yolo.h"

char const * HELLO = "HELLO";

void hello(void)
{
	message(__func__, __FILE__);
}
