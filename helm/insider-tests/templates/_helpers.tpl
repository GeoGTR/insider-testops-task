{{/*
Expand the name of the chart.
*/}}
{{- define "insider-tests.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "insider-tests.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "insider-tests.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "insider-tests.labels" -}}
helm.sh/chart: {{ include "insider-tests.chart" . }}
{{ include "insider-tests.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "insider-tests.selectorLabels" -}}
app.kubernetes.io/name: {{ include "insider-tests.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Chrome node specific labels
*/}}
{{- define "insider-tests.chromeNodeLabels" -}}
{{ include "insider-tests.labels" . }}
app.kubernetes.io/component: chrome-node
app.kubernetes.io/part-of: insider-tests
{{- end }}

{{/*
Chrome node selector labels
*/}}
{{- define "insider-tests.chromeNodeSelectorLabels" -}}
{{ include "insider-tests.selectorLabels" . }}
app.kubernetes.io/component: chrome-node
{{- end }}

{{/*
Test controller specific labels
*/}}
{{- define "insider-tests.testControllerLabels" -}}
{{ include "insider-tests.labels" . }}
app.kubernetes.io/component: test-controller
app.kubernetes.io/part-of: insider-tests
{{- end }}

{{/*
Test controller selector labels
*/}}
{{- define "insider-tests.testControllerSelectorLabels" -}}
{{ include "insider-tests.selectorLabels" . }}
app.kubernetes.io/component: test-controller
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "insider-tests.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "insider-tests.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}
