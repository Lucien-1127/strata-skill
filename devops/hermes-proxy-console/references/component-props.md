# Hermes Proxy Console — Component Props 契約

## StatCard

```typescript
import type { KPIItem } from '@/types/metric';

export interface StatCardProps {
  item: KPIItem;
  onClick?: (item: KPIItem) => void;
}
```

## DashboardTabs

```typescript
import type { DashboardTabKey } from '@/types/dashboard';

export interface DashboardTabsProps {
  activeTab: DashboardTabKey;
  onChange: (tab: DashboardTabKey) => void;
  alertCount?: number;
}
```

## AlertsList

```typescript
import type { AlertItem } from '@/types/alert';

export interface AlertsListProps {
  items: AlertItem[];
  onAlertClick: (alert: AlertItem) => void;
  onActionClick: (alert: AlertItem, action: string) => void;
}
```

## EventsTimeline

```typescript
import type { TimelineEvent } from '@/types/event';

export interface EventsTimelineProps {
  items: TimelineEvent[];
  onEventClick?: (event: TimelineEvent) => void;
}
```

## TrendPanel

```typescript
import type { TrendRangeKey, TrendSeries } from '@/types/dashboard';

export interface TrendPanelProps {
  range: TrendRangeKey;
  series: TrendSeries[];
  onRangeChange: (range: TrendRangeKey) => void;
}
```
