APP_NAME := langgraph-example
CHART_DIR := ./$(APP_NAME)

.PHONY: package lint dry-run install upgrade uninstall clean

package:
	helm package $(CHART_DIR)

lint:
	helm lint $(CHART_DIR)

dry-run:
	helm install --dry-run --debug $(APP_NAME) $(CHART_DIR)

install: package
	helm install $(APP_NAME) $(CHART_DIR)

upgrade: package
	helm upgrade $(APP_NAME) $(CHART_DIR)

uninstall:
	helm uninstall $(APP_NAME)

clean:
	rm -f $(APP_NAME)-*.tgz
