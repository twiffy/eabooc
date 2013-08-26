# Makefile for deploying to stage and production
#

stage:
	git status
	git diff staged --stat
	@echo "Going to deploy to STAGING: https://booc-stage.appspot.com/"
	sleep 5
	git push . -f HEAD:staged
	appcfg update . --email booc.class -A booc-stage

deploy:
	git status
	git diff deployed --stat
	@echo
	@echo "Going to deploy to PRODUCTION: https://booc-iu.appspot.com/"
	@echo
	sleep 7
	git push . -f HEAD:deployed
	appcfg update . --email booc.class
