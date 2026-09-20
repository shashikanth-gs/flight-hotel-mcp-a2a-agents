{{- define "flight-hotel-mcp-a2a.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "flight-hotel-mcp-a2a.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "flight-hotel-mcp-a2a.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "flight-hotel-mcp-a2a.componentName" -}}
{{- printf "%s-%s" (include "flight-hotel-mcp-a2a.fullname" .root) .component | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "flight-hotel-mcp-a2a.commonLabels" -}}
helm.sh/chart: {{ include "flight-hotel-mcp-a2a.chart" . | quote }}
app.kubernetes.io/name: {{ include "flight-hotel-mcp-a2a.name" . | quote }}
app.kubernetes.io/instance: {{ .Release.Name | quote }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service | quote }}
{{- end -}}

{{- define "flight-hotel-mcp-a2a.componentLabels" -}}
{{ include "flight-hotel-mcp-a2a.commonLabels" .root }}
app.kubernetes.io/component: {{ .component | quote }}
{{- end -}}

{{- define "flight-hotel-mcp-a2a.selectorLabels" -}}
app.kubernetes.io/name: {{ include "flight-hotel-mcp-a2a.name" .root | quote }}
app.kubernetes.io/instance: {{ .root.Release.Name | quote }}
app.kubernetes.io/component: {{ .component | quote }}
{{- end -}}

{{- define "flight-hotel-mcp-a2a.image" -}}
{{- $tag := default .root.Values.global.imageTag .image.tag -}}
{{- printf "%s:%s" .image.repository $tag -}}
{{- end -}}

{{- define "flight-hotel-mcp-a2a.nvidiaSecretName" -}}
{{- default (include "flight-hotel-mcp-a2a.componentName" (dict "root" . "component" "nvidia")) .Values.nvidia.existingSecret -}}
{{- end -}}
