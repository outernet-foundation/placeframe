#include <DotNet/Unity/Mathematics/uint3.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>

namespace DotNet::Unity::Mathematics {
struct uint3;
}

namespace DotNet::Unity::Mathematics {

void (*uint3::Construct_fwI58ky8hlqSzCrUJCqq4Q)(::std::uint32_t x, ::std::uint32_t y, ::std::uint32_t z, ::DotNet::Unity::Mathematics::uint3* pReturnValue, void** reinteropException) = nullptr;


uint3 uint3::Construct(::std::uint32_t x, ::std::uint32_t y, ::std::uint32_t z)
{
    void* reinteropException = nullptr;
    uint3 result;
    Construct_fwI58ky8hlqSzCrUJCqq4Q(x, y, z, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


