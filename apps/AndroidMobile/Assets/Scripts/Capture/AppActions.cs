using System;
using System.Collections.Generic;
using FofX.Stateful;
using Placeframe.Client;

namespace Placeframe.Client
{
    public class SetCaptureStatusAction : ObservableNodeAction<AppState>
    {
        private static Dictionary<CaptureStatus, CaptureStatus> _validTransitions = new Dictionary<CaptureStatus, CaptureStatus>()
        {
            { CaptureStatus.Idle,  CaptureStatus.Starting  },
            { CaptureStatus.Starting,  CaptureStatus.Capturing  },
            { CaptureStatus.Capturing,  CaptureStatus.Stopping  },
            { CaptureStatus.Stopping,  CaptureStatus.Idle  }
        };

        private CaptureStatus _status;

        public SetCaptureStatusAction(CaptureStatus status)
        {
            _status = status;
        }

        public override void Execute(AppState target)
        {
            if (target.captureStatus.value == _status)
                return;

            if (_validTransitions.TryGetValue(target.captureStatus.value, out var toStatus) && toStatus != _status)
                throw new Exception($"Cannot transition from {target.captureStatus.value} to {_status}");

            target.captureStatus.value = _status;
        }
    }
}