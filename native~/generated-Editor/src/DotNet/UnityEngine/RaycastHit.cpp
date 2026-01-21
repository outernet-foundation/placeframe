#include <DotNet/UnityEngine/RaycastHit.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEngine/Transform.h>
#include <cstdint>
#include <DotNet/UnityEngine/Vector3.h>

namespace DotNet::UnityEngine {
struct RaycastHit;
}
namespace DotNet::UnityEngine {
struct Vector3;
}

namespace DotNet::UnityEngine {

void (*RaycastHit::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(::DotNet::UnityEngine::RaycastHit* pReturnValue, void** reinteropException) = nullptr;


RaycastHit RaycastHit::Construct()
{
    void* reinteropException = nullptr;
    RaycastHit result;
    Construct_1B2M2Y8AsgTpgAmY7PhCfg(&result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void* (*DotNet::UnityEngine::RaycastHit::Property_get_transform)(const ::DotNet::UnityEngine::RaycastHit* thiz, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Transform RaycastHit::transform() const {
    void* reinteropException = nullptr;
    auto result = Property_get_transform(&(*this), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::UnityEngine::Transform(::DotNet::Reinterop::ObjectHandle(result));
}


::std::int32_t (*DotNet::UnityEngine::RaycastHit::Property_get_triangleIndex)(const ::DotNet::UnityEngine::RaycastHit* thiz, void** reinteropException) = nullptr;


::std::int32_t RaycastHit::triangleIndex() const {
    void* reinteropException = nullptr;
    auto result = Property_get_triangleIndex(&(*this), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEngine::RaycastHit::Property_get_point)(const ::DotNet::UnityEngine::RaycastHit* thiz, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Vector3 RaycastHit::point() const {
    void* reinteropException = nullptr;
    ::DotNet::UnityEngine::Vector3 result;
    Property_get_point(&(*this), &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEngine::RaycastHit::Property_set_point)(const ::DotNet::UnityEngine::RaycastHit* thiz, const ::DotNet::UnityEngine::Vector3* value, void** reinteropException) = nullptr;


void RaycastHit::point(const ::DotNet::UnityEngine::Vector3& value) const {
    void* reinteropException = nullptr;
    Property_set_point(&(*this), &value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


} // namespace DotNet::UnityEngine


