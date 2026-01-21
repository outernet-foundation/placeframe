#include <DotNet/Unity/Mathematics/int4x4.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/Unity/Mathematics/int4.h>

namespace DotNet::Unity::Mathematics {
struct int4;
}
namespace DotNet::Unity::Mathematics {
struct int4x4;
}

namespace DotNet::Unity::Mathematics {

void (*int4x4::Construct___u7bLaYK7NsvS7W3VaLQcw)(const ::DotNet::Unity::Mathematics::int4* c0, const ::DotNet::Unity::Mathematics::int4* c1, const ::DotNet::Unity::Mathematics::int4* c2, const ::DotNet::Unity::Mathematics::int4* c3, ::DotNet::Unity::Mathematics::int4x4* pReturnValue, void** reinteropException) = nullptr;


int4x4 int4x4::Construct(const ::DotNet::Unity::Mathematics::int4& c0, const ::DotNet::Unity::Mathematics::int4& c1, const ::DotNet::Unity::Mathematics::int4& c2, const ::DotNet::Unity::Mathematics::int4& c3)
{
    void* reinteropException = nullptr;
    int4x4 result;
    Construct___u7bLaYK7NsvS7W3VaLQcw(&c0, &c1, &c2, &c3, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


