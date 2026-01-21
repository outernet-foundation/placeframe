#include <DotNet/UnityEngine/Vector2.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>

namespace DotNet::UnityEngine {
struct Vector2;
}

namespace DotNet::UnityEngine {

void (*Vector2::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(::DotNet::UnityEngine::Vector2* pReturnValue, void** reinteropException) = nullptr;


Vector2 Vector2::Construct()
{
    void* reinteropException = nullptr;
    Vector2 result;
    Construct_1B2M2Y8AsgTpgAmY7PhCfg(&result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::UnityEngine


