#include <stdio.h>
#include <string.h>

#include "hello.h"
#include "test/yolo.h"
#include "yolo.h"

void demo(void)
{
	message(__func__, __FILE__);
}

int main(void)
{
	demo();
	hello();
	yolo();

	char const * hey = HELLO;
	char const * yo1 = YOLO_1;
	char const * yo2 = YOLO_2;

	if (strcmp(hey, "HELLO") != 0)
	{
		printf("Expected '%s', Found '%s'\r\n", "HELLO", hey);
	}
	else if (strcmp(yo1, "YOLO_1") != 0)
	{
		printf("Expected '%s', Found '%s'\r\n", "YOLO_1", yo1);
	}
	else if (strcmp(yo2, "YOLO_2") != 0)
	{
		printf("Expected '%s', Found '%s'\r\n", "YOLO_2", yo2);
	}
	else
	{
		printf("Successfully linked extern variables: [ '%s', '%s', '%s' ]\r\n", hey, yo1, yo2);
	}

	return 0;
}
