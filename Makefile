CC 			:= g++ # This is the main compiler
SRCDIR 			:= src
BUILDDIR 		:= build
TARGET 			:= bin/run-cgopt 
SRCEXT 			:= cpp
SOURCES 		:= $(shell find $(SRCDIR) -type f -name *.$(SRCEXT))
OBJECTS 		:= $(patsubst $(SRCDIR)/%,$(BUILDDIR)/%,$(SOURCES:.$(SRCEXT)=.o))
CFLAGS 			:= -Wall -O2 -std=c++11 -g
LIB 			:= -lpthread -lyaml -Wl,--as-needed
INC 			:= -I include 
SUBMODPATHS 		:= protobuf worker msgqueue


$(TARGET): $(OBJECTS)
	@echo " Linking..."
	@echo " $(CC) $^ -o $(TARGET) $(LIB)"; $(CC) $^ -o $(TARGET) $(LIB)

$(BUILDDIR)/%.o: $(SRCDIR)/%.$(SRCEXT)
	@echo " Building..."
	@mkdir -p $(BUILDDIR)
	@echo " $(CC) $(CFLAGS) $(INC) -c -o $@ $<"; $(CC) $(CFLAGS) $(INC) -c -o $@ $<

clean:
	@echo " Cleaning..."; 
	@echo " $(RM) -r $(BUILDDIR) $(TARGET)"; $(RM) -r $(BUILDDIR) $(TARGET)


# Tests
test:
	@echo " Building tests..."; 
	$(CC) $(CFLAGS) test/testsuite.cpp $(INC) $(LIB) -o bin/test
	@echo " Running tests..."; 
	
	
submodules:
	-for d in $(SUBMODPATHS); do ($(MAKE) -C $$d); done

cleanall:
	@echo " Cleaning submodules..."; 
	-for d in $(SUBMODPATHS); do ($(MAKE) -C $$d clean); done

.PHONY: clean cleanall submodules
	
