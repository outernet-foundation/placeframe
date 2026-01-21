#include <DotNet/UnityEngine/Matrix4x4.h>
#include <DotNet/UnityEngine/Vector3.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>

namespace DotNet::UnityEngine {
struct Vector3;
}

namespace DotNet::UnityEngine {

void (*DotNet::UnityEngine::Matrix4x4::CallMultiplyPoint3x4_nRoP5wpLbrdr_ZZudXtbFA)(const ::DotNet::UnityEngine::Matrix4x4* thiz, const ::DotNet::UnityEngine::Vector3* point, ::DotNet::UnityEngine::Vector3* pReturnValue, void** reinteropException) = nullptr;


::DotNet::UnityEngine::Vector3 Matrix4x4::MultiplyPoint3x4(const ::DotNet::UnityEngine::Vector3& point) const {
    void* reinteropException = nullptr;
    ::DotNet::UnityEngine::Vector3 result;
    CallMultiplyPoint3x4_nRoP5wpLbrdr_ZZudXtbFA(&(*this), &point, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::UnityEngine


