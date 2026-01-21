#include <DotNet/Unity/Mathematics/int2.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>

namespace DotNet::Unity::Mathematics {
struct int2;
}

namespace DotNet::Unity::Mathematics {

void (*int2::Construct_CSSfw_WOk6__K5__v8pO4eLw)(::std::int32_t x, ::std::int32_t y, ::DotNet::Unity::Mathematics::int2* pReturnValue, void** reinteropException) = nullptr;


int2 int2::Construct(::std::int32_t x, ::std::int32_t y)
{
    void* reinteropException = nullptr;
    int2 result;
    Construct_CSSfw_WOk6__K5__v8pO4eLw(x, y, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


