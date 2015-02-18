PP			    = g++
RM			    = rm -f
CPPFLAGS		= -Wall -I. -O2 -std=c++14 -g
LDFLAGS			= -lpthread -lzmqpp -lzmq  -Wl,--no-as-needed
SOURCES			= $(wildcard *.cpp)
TARGETS			= $(SOURCES:%.cpp=%)

all:	${TARGETS}

clean:
	${RM} *.obj *~* ${TARGETS}

${TARGETS}:
	${CPP} ${CPPFLAGS} -o $@ ${@:%=%.cpp} ${LDFLAGS}
