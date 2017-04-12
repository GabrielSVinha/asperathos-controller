# Controller Plugin - "single"

## Start Scaling

Request body:
```javascript
{
	"plugin":<scaling plugin>,
	"actuator":<actuation plugin>,
	"metric_source":<metrics plugin>,
	"instances":["vm_id0", "vm_id1"],
	"scaling-parameter-key0":"scaling-parameter-value0",
	...
	"scaling-parameter-keyN":"scaling-parameter-valueN"
}
```
### Expected parameters

#### **check_interval**

Time between application state checks, in seconds. The controller checks the application state every check_interval seconds.

#### **trigger_down**

The absolute value of the difference between job progress and time progress that triggers the scale down.

#### **trigger_up**

The absolute value of the difference between job progress and time progress that triggers the scale up. 

#### **min_cap**

The minimum possible value of resources that can be allocated to the application. Must be in range [0,100].

#### **max_cap**

The maximum possible value of resources that can be allocated to the application. Must be in range [0,100].

#### **actuation_size**

Amount of resources added or removed when scaling up or down. Must be in range [0,100].

#### **metric_rounding**

The amount of decimal digits considered when taking scaling decisions.
e.g.: If the scaler gets a metric value 0.567 from the metric source and metric_rounding = 2 then the value the scaler will use is 0.57.
