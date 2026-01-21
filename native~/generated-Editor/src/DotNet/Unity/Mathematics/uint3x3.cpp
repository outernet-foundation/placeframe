#include <DotNet/Unity/Mathematics/uint3x3.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/Unity/Mathematics/uint3.h>

namespace DotNet::Unity::Mathematics {
struct uint3;
}
namespace DotNet::Unity::Mathematics {
struct uint3x3;
}

namespace DotNet::Unity::Mathematics {

void (*uint3x3::Construct_ZtWpbr50zCN2kT2S7fwByQ)(const ::DotNet::Unity::Mathematics::uint3* c0, const ::DotNet::Unity::Mathematics::uint3* c1, const ::DotNet::Unity::Mathematics::uint3* c2, ::DotNet::Unity::Mathematics::uint3x3* pReturnValue, void** reinteropException) = nullptr;


uint3x3 uint3x3::Construct(const ::DotNet::Unity::Mathematics::uint3& c0, const ::DotNet::Unity::Mathematics::uint3& c1, const ::DotNet::Unity::Mathematics::uint3& c2)
{
    void* reinteropException = nullptr;
    uint3x3 result;
    Construct_ZtWpbr50zCN2kT2S7fwByQ(&c0, &c1, &c2, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


