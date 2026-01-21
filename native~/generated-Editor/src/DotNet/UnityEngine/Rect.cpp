#include <DotNet/UnityEngine/Rect.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>

namespace DotNet::UnityEngine {
struct Rect;
}

namespace DotNet::UnityEngine {

void (*Rect::Construct_SWzoP__nNh7g2zNwjI5mUvQ)(float x, float y, float width, float height, ::DotNet::UnityEngine::Rect* pReturnValue, void** reinteropException) = nullptr;


Rect Rect::Construct(float x, float y, float width, float height)
{
    void* reinteropException = nullptr;
    Rect result;
    Construct_SWzoP__nNh7g2zNwjI5mUvQ(x, y, width, height, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::UnityEngine


