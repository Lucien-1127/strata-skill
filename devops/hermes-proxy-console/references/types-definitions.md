# Hermes Proxy Console — TypeScript 型別定義

## common.ts

```typescript
export type ID = string;
export type AppEnvironment = 'prod' | 'staging' | 'dev';
export type HealthStatus = 'online' | 'degraded' | 'offline' | 'warning' | 'down' | 'idle' | 'busy' | 'failed';
export type SeverityLevel = 'critical' | 'warning' | 'info' | 'resolved';
export type AsyncState = 'idle' | 'loading' | 'success' | 'error';

export interface BaseEntity {
  id: ID;
  createdAt: string;
  updatedAt: string;
}
```

## metric.ts

```typescript
import type { HealthStatus, ID } from './common';

export type MetricUnit = 'count' | 'percent' | 'ms' | 'rpm' | 'bytes' | 'gb' | 'quota';

export interface MetricDelta {
  value: number;
  direction: 'up' | 'down' | 'flat';
  percentage?: number;
  comparedTo?: string;
}

export interface KPIItem {
  id: ID;
  key: 'vm_status' | 'proxy_status' | 'active_agents' | 'requests_per_minute'
       | 'avg_latency' | 'error_rate' | 'quota_usage' | 'alerts_count';
  label: string;
  value: string | number;
  rawValue?: number;
  unit?: MetricUnit;
  status?: HealthStatus;
  delta?: MetricDelta;
  description?: string;
  clickable?: boolean;
  targetRoute?: string;
}
```

## alert.ts

```typescript
import type { BaseEntity, ID, SeverityLevel } from './common';

export type AlertSourceType = 'vm' | 'proxy' | 'agent' | 'rule' | 'quota' | 'system';
export type AlertActionType = 'acknowledge' | 'ignore' | 'restart_proxy' | 'open_logs' | 'assign' | 'resolve';

export interface AlertItem extends BaseEntity {
  sourceType: AlertSourceType;
  sourceId: ID;
  sourceName: string;
  severity: SeverityLevel;
  title: string;
  summary: string;
  occurredAt: string;
  isRead: boolean;
  isResolved: boolean;
  requestId?: string;
  logUrl?: string;
  availableActions: AlertActionType[];
}

export interface AlertSummary {
  total: number;
  critical: number;
  warning: number;
  info: number;
  resolved: number;
}
```

## event.ts

```typescript
import type { BaseEntity, ID } from './common';

export type AuditResult = 'success' | 'failed' | 'partial';

export interface EventActor {
  id: ID;
  name: string;
  avatarUrl?: string;
  ip?: string;
}

export interface EventTarget {
  id: ID;
  type: 'vm' | 'proxy' | 'agent' | 'rule' | 'quota' | 'setting';
  name: string;
}

export interface TimelineEvent extends BaseEntity {
  actor: EventActor;
  action: string;
  target: EventTarget;
  result: AuditResult;
  timestamp: string;
  detail?: string;
}
```

## proxy.ts

```typescript
import type { BaseEntity, HealthStatus, ID } from './common';

export type ProxyAction = 'start' | 'stop' | 'restart' | 'reload_config' | 'switch_version' | 'view_logs';

export interface ProxyRuntime extends BaseEntity {
  name: string;
  vmId: ID;
  vmName: string;
  version: string;
  status: HealthStatus;
  connectionCount: number;
  queueLength: number;
  avgProcessingMs: number;
  errorRate: number;
  startedAt?: string;
  heartbeatAt?: string;
  availableActions: ProxyAction[];
}
```

## vm.ts

```typescript
import type { BaseEntity, HealthStatus } from './common';

export interface VmResourceUsage {
  cpuPercent: number;
  ramPercent: number;
  diskPercent: number;
  networkInMbps: number;
  networkOutMbps: number;
}

export interface VmInstance extends BaseEntity {
  name: string;
  projectId: string;
  zone: string;
  externalIp?: string;
  internalIp: string;
  status: HealthStatus;
  heartbeatAt?: string;
  usage: VmResourceUsage;
}
```

## dashboard.ts

```typescript
import type { AppEnvironment } from './common';
import type { AlertItem, AlertSummary } from './alert';
import type { TimelineEvent } from './event';
import type { KPIItem } from './metric';
import type { ProxyRuntime } from './proxy';

export type DashboardTabKey = 'trends' | 'alerts' | 'events';
export type TrendRangeKey = '1h' | '6h' | '24h' | '7d';

export interface TimeSeriesPoint {
  timestamp: string;
  value: number;
}

export interface TrendSeries {
  key: 'requests' | 'latency' | 'error_rate' | 'quota_usage';
  label: string;
  color: string;
  points: TimeSeriesPoint[];
  unit: 'rpm' | 'ms' | 'percent' | 'quota';
}

export interface DashboardOverview {
  environment: AppEnvironment;
  generatedAt: string;
  kpis: KPIItem[];
  alertSummary: AlertSummary;
  latestProxy?: ProxyRuntime;
}

export interface DashboardPayload {
  overview: DashboardOverview;
  trendRange: TrendRangeKey;
  trends: TrendSeries[];
  alerts: AlertItem[];
  events: TimelineEvent[];
}
```

## telegram.ts

```typescript
export interface TelegramThemeState {
  colorScheme: 'light' | 'dark';
  bgColor?: string;
  textColor?: string;
  hintColor?: string;
  linkColor?: string;
  buttonColor?: string;
  buttonTextColor?: string;
  secondaryBgColor?: string;
}

export interface TelegramViewportState {
  width: number;
  height: number;
  isExpanded: boolean;
  isStable: boolean;
}

export interface MainButtonConfig {
  text: string;
  isVisible: boolean;
  isEnabled: boolean;
  isLoading?: boolean;
  hasShineEffect?: boolean;
  onClick?: () => void;
}

export interface BackButtonConfig {
  isVisible: boolean;
  onClick?: () => void;
}

export interface SettingsButtonConfig {
  isVisible: boolean;
  onClick?: () => void;
}
```

## api.ts

```typescript
import type { DashboardPayload } from './dashboard';

export interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string;
  requestId?: string;
}

export interface ApiError {
  code: string;
  message: string;
  requestId?: string;
  details?: unknown;
}

export type DashboardResponse = ApiResponse<DashboardPayload>;
```
