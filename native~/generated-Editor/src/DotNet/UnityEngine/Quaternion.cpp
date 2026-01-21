#include <DotNet/UnityEngine/Quaternion.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEngine/Vector3.h>

namespace DotNet::UnityEngine {
struct Quaternion;
}
namespace DotNet::UnityEngine {
struct Vector3;
}

namespace DotNet::UnityEngine {

void (*Quaternion::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(::DotNet::UnityEngine::Quaternion* pReturnValue, void** reinteropException) = nullptr;


Quaternion Quaternion::Construct()
{
    void* reinteropException = nullptr;
    Quaternion result;
    Construct_1B2M2Y8AsgTpgAmY7PhCfg(&result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEngine::Quaternion::CallLookRotation_7YsCImhRrFIh_6hqa__5IAQ)(const ::DotNet::UnityEngine::Vector3* forward, const ::DotNet::UnityEngine::Vector3* upwards, ::DotNet::UnityEngine::Quaternion* pReturnValue, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Quaternion Quaternion::LookRotation(const ::DotNet::UnityEngine::Vector3& forward, const ::DotNet::UnityEngine::Vector3& upwards) {
    void* reinteropException = nullptr;
    ::DotNet::UnityEngine::Quaternion result;
    CallLookRotation_7YsCImhRrFIh_6hqa__5IAQ(&forward, &upwards, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::UnityEngine


