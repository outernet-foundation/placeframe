#include <DotNet/UnityEngine/Vector3.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>

namespace DotNet::UnityEngine {
struct Vector3;
}

namespace DotNet::UnityEngine {

void (*Vector3::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException) = nullptr;


Vector3 Vector3::Construct()
{
    void* reinteropException = nullptr;
    Vector3 result;
    Construct_1B2M2Y8AsgTpgAmY7PhCfg(&result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*Vector3::Construct_LB__scTJntm1swre2IwXuIw)(float x, float y, float z, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException) = nullptr;


Vector3 Vector3::Construct(float x, float y, float z)
{
    void* reinteropException = nullptr;
    Vector3 result;
    Construct_LB__scTJntm1swre2IwXuIw(x, y, z, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEngine::Vector3::Property_get_forward)(::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Vector3 Vector3::forward() {
    void* reinteropException = nullptr;
    ::DotNet::UnityEngine::Vector3 result;
    Property_get_forward(&result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEngine::Vector3::Property_get_up)(::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Vector3 Vector3::up() {
    void* reinteropException = nullptr;
    ::DotNet::UnityEngine::Vector3 result;
    Property_get_up(&result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEngine::Vector3::Property_get_zero)(::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Vector3 Vector3::zero() {
    void* reinteropException = nullptr;
    ::DotNet::UnityEngine::Vector3 result;
    Property_get_zero(&result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::UnityEngine


