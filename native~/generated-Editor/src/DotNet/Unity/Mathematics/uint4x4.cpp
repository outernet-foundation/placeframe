#include <DotNet/Unity/Mathematics/uint4x4.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/Unity/Mathematics/uint4.h>

namespace DotNet::Unity::Mathematics {
struct uint4;
}
namespace DotNet::Unity::Mathematics {
struct uint4x4;
}

namespace DotNet::Unity::Mathematics {

void (*uint4x4::Construct_P__muY59YdYGI7W2ynF5sPw)(const ::DotNet::Unity::Mathematics::uint4* c0, const ::DotNet::Unity::Mathematics::uint4* c1, const ::DotNet::Unity::Mathematics::uint4* c2, const ::DotNet::Unity::Mathematics::uint4* c3, ::DotNet::Unity::Mathematics::uint4x4* pReturnValue, void** reinteropException) = nullptr;


uint4x4 uint4x4::Construct(const ::DotNet::Unity::Mathematics::uint4& c0, const ::DotNet::Unity::Mathematics::uint4& c1, const ::DotNet::Unity::Mathematics::uint4& c2, const ::DotNet::Unity::Mathematics::uint4& c3)
{
    void* reinteropException = nullptr;
    uint4x4 result;
    Construct_P__muY59YdYGI7W2ynF5sPw(&c0, &c1, &c2, &c3, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


