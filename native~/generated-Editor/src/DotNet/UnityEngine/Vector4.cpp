#include <DotNet/UnityEngine/Vector4.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>

namespace DotNet::UnityEngine {
struct Vector4;
}

namespace DotNet::UnityEngine {

void (*Vector4::Construct_HRdOMAw1wcknBRlYiWJ61Q)(float x, float y, float z, float w, ::DotNet::UnityEngine::Vector4* pReturnValue, void** reinteropException) = nullptr;


Vector4 Vector4::Construct(float x, float y, float z, float w)
{
    void* reinteropException = nullptr;
    Vector4 result;
    Construct_HRdOMAw1wcknBRlYiWJ61Q(x, y, z, w, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*Vector4::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(::DotNet::UnityEngine::Vector4* pReturnValue, void** reinteropException) = nullptr;


Vector4 Vector4::Construct()
{
    void* reinteropException = nullptr;
    Vector4 result;
    Construct_1B2M2Y8AsgTpgAmY7PhCfg(&result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::UnityEngine


