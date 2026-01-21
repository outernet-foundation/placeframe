#include <DotNet/Unity/Mathematics/int2x2.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/Unity/Mathematics/int2.h>

namespace DotNet::Unity::Mathematics {
struct int2;
}
namespace DotNet::Unity::Mathematics {
struct int2x2;
}

namespace DotNet::Unity::Mathematics {

void (*int2x2::Construct_mnOQ_opjj2StriajDwrD9g)(const ::DotNet::Unity::Mathematics::int2* c0, const ::DotNet::Unity::Mathematics::int2* c1, ::DotNet::Unity::Mathematics::int2x2* pReturnValue, void** reinteropException) = nullptr;


int2x2 int2x2::Construct(const ::DotNet::Unity::Mathematics::int2& c0, const ::DotNet::Unity::Mathematics::int2& c1)
{
    void* reinteropException = nullptr;
    int2x2 result;
    Construct_mnOQ_opjj2StriajDwrD9g(&c0, &c1, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


