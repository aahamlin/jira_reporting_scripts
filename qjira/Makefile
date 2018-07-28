SUBDIRS = commands

clean:
	rm -fr __pycache__
	rm -f *.pyc
	for dir in $(SUBDIRS); do \
		$(MAKE) -C $$dir $@; \
	done

.PHONY: clean
