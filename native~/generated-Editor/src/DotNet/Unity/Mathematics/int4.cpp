#include <DotNet/Unity/Mathematics/int4.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>

namespace DotNet::Unity::Mathematics {
struct int4;
}

namespace DotNet::Unity::Mathematics {

void (*int4::Construct_ima1GH0lko9R2DnR_aRPyw)(::std::int32_t x, ::std::int32_t y, ::std::int32_t z, ::std::int32_t w, ::DotNet::Unity::Mathematics::int4* pReturnValue, void** reinteropException) = nullptr;


int4 int4::Construct(::std::int32_t x, ::std::int32_t y, ::std::int32_t z, ::std::int32_t w)
{
    void* reinteropException = nullptr;
    int4 result;
    Construct_ima1GH0lko9R2DnR_aRPyw(x, y, z, w, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


