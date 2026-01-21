#include <DotNet/Unity/Mathematics/uint4.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>

namespace DotNet::Unity::Mathematics {
struct uint4;
}

namespace DotNet::Unity::Mathematics {

void (*uint4::Construct_cx5C8OyRaFgckdYoG5u6cw)(::std::uint32_t x, ::std::uint32_t y, ::std::uint32_t z, ::std::uint32_t w, ::DotNet::Unity::Mathematics::uint4* pReturnValue, void** reinteropException) = nullptr;


uint4 uint4::Construct(::std::uint32_t x, ::std::uint32_t y, ::std::uint32_t z, ::std::uint32_t w)
{
    void* reinteropException = nullptr;
    uint4 result;
    Construct_cx5C8OyRaFgckdYoG5u6cw(x, y, z, w, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


