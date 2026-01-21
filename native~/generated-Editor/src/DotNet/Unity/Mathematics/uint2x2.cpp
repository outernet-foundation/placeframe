#include <DotNet/Unity/Mathematics/uint2x2.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/Unity/Mathematics/uint2.h>

namespace DotNet::Unity::Mathematics {
struct uint2;
}
namespace DotNet::Unity::Mathematics {
struct uint2x2;
}

namespace DotNet::Unity::Mathematics {

void (*uint2x2::Construct_P1cAnApbSLA3Xc3DztNMzw)(const ::DotNet::Unity::Mathematics::uint2* c0, const ::DotNet::Unity::Mathematics::uint2* c1, ::DotNet::Unity::Mathematics::uint2x2* pReturnValue, void** reinteropException) = nullptr;


uint2x2 uint2x2::Construct(const ::DotNet::Unity::Mathematics::uint2& c0, const ::DotNet::Unity::Mathematics::uint2& c1)
{
    void* reinteropException = nullptr;
    uint2x2 result;
    Construct_P1cAnApbSLA3Xc3DztNMzw(&c0, &c1, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


