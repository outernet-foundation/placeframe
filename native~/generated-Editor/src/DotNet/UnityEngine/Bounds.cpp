#include <DotNet/UnityEngine/Bounds.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/UnityEngine/Vector3.h>

namespace DotNet::UnityEngine {
struct Vector3;
}
namespace DotNet::UnityEngine {
struct Bounds;
}

namespace DotNet::UnityEngine {

void (*Bounds::Construct_Qy9aU2ShAPtxkIq6r1DXbA)(const ::DotNet::UnityEngine::Vector3* center, const ::DotNet::UnityEngine::Vector3* size, ::DotNet::UnityEngine::Bounds* pReturnValue, void** reinteropException) = nullptr;


Bounds Bounds::Construct(const ::DotNet::UnityEngine::Vector3& center, const ::DotNet::UnityEngine::Vector3& size)
{
    void* reinteropException = nullptr;
    Bounds result;
    Construct_Qy9aU2ShAPtxkIq6r1DXbA(&center, &size, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::UnityEngine


