#include <DotNet/Unity/Mathematics/uint2.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>

namespace DotNet::Unity::Mathematics {
struct uint2;
}

namespace DotNet::Unity::Mathematics {

void (*uint2::Construct_41DRfMZ91WmKUsGkzEnbPw)(::std::uint32_t x, ::std::uint32_t y, ::DotNet::Unity::Mathematics::uint2* pReturnValue, void** reinteropException) = nullptr;


uint2 uint2::Construct(::std::uint32_t x, ::std::uint32_t y)
{
    void* reinteropException = nullptr;
    uint2 result;
    Construct_41DRfMZ91WmKUsGkzEnbPw(x, y, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


