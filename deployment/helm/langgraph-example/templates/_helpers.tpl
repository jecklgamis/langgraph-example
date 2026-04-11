{{- define "langgraph-example.name" -}}
{{- .Chart.Name }}
{{- end }}

{{- define "langgraph-example.fullname" -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "langgraph-example.labels" -}}
app.kubernetes.io/name: {{ include "langgraph-example.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "langgraph-example.selectorLabels" -}}
app.kubernetes.io/name: {{ include "langgraph-example.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
