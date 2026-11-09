# nebius-gpu-autoscaler

Long-running controller that reconciles Nebius GPU instances against unschedulable reconstructor pods: creates an instance when reconstruction work cannot be scheduled, deletes it once the node has been idle, and enforces a hard maximum instance lifetime so a reconciliation bug cannot leave a GPU running indefinitely.
