# Makefile for deploying to stage and production
#

stage:
	git push . -f HEAD:staged
	appcfg update . --email booc.class -A booc-stage

deploy:
	git push . -f HEAD:deployed
	appcfg update . --email booc.class
