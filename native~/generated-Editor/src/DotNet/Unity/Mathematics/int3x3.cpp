#include <DotNet/Unity/Mathematics/int3x3.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/Unity/Mathematics/int3.h>

namespace DotNet::Unity::Mathematics {
struct int3;
}
namespace DotNet::Unity::Mathematics {
struct int3x3;
}

namespace DotNet::Unity::Mathematics {

void (*int3x3::Construct_A__Tj4TB5T_s22Xd4RW46Fg)(const ::DotNet::Unity::Mathematics::int3* c0, const ::DotNet::Unity::Mathematics::int3* c1, const ::DotNet::Unity::Mathematics::int3* c2, ::DotNet::Unity::Mathematics::int3x3* pReturnValue, void** reinteropException) = nullptr;


int3x3 int3x3::Construct(const ::DotNet::Unity::Mathematics::int3& c0, const ::DotNet::Unity::Mathematics::int3& c1, const ::DotNet::Unity::Mathematics::int3& c2)
{
    void* reinteropException = nullptr;
    int3x3 result;
    Construct_A__Tj4TB5T_s22Xd4RW46Fg(&c0, &c1, &c2, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


