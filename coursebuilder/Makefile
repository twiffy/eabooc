# Makefile for deploying to stage and production
#

certs:
	curl http://ci.kennethreitz.org/job/ca-bundle/lastSuccessfulBuild/artifact/cacerts.pem -o lib/cacert.pem


no-sandbox:
	if [ -f controllers/sandbox.py ]; then exit 1; fi

stage: no-sandbox
	git status
	git diff --quiet --exit-code
	git diff --cached --quiet --exit-code
	git diff staged --stat
	@echo "Going to deploy to STAGING: https://booc-stage.appspot.com/"
	sleep 5
	appcfg update . --email booc.class -A booc-stage
	#git stash apply stash^{/APPSTATS2}
	#appcfg update . --email booc.class -A booc-stage -V stats
	#git checkout -- app.yaml appengine_config.py
	git push . -f HEAD:staged

deploy: no-sandbox
	git status
	git diff --quiet --exit-code
	git diff --cached --quiet --exit-code
	git diff deployed --stat
	@echo
	@echo "Going to deploy to PRODUCTION:"
	@head -1 app.yaml
	@echo
	sleep 7
	appcfg update . --email booc.class
	#git stash apply stash^{/APPSTATS2}
	#appcfg update . --email booc.class -V stats
	#git checkout -- app.yaml appengine_config.py
	git push . -f HEAD:deployed

badge-dep:
	git diff --quiet --exit-code
	git diff --cached --quiet --exit-code
	git diff badge-dep --stat
	@echo
	@echo "Going to deploy to BADGE-ish PRODUCTION-ish: https://badges-dot-eabooc.appspot.com/"
	@echo
	sleep 5
	appcfg update . --email booc.class -V badges
	git push . -f HEAD:badge-dep

