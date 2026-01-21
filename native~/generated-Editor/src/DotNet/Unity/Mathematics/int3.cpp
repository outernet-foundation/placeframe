#include <DotNet/Unity/Mathematics/int3.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>

namespace DotNet::Unity::Mathematics {
struct int3;
}

namespace DotNet::Unity::Mathematics {

void (*int3::Construct_2lzDmp63Mfw__oFMy0HdgWw)(::std::int32_t x, ::std::int32_t y, ::std::int32_t z, ::DotNet::Unity::Mathematics::int3* pReturnValue, void** reinteropException) = nullptr;


int3 int3::Construct(::std::int32_t x, ::std::int32_t y, ::std::int32_t z)
{
    void* reinteropException = nullptr;
    int3 result;
    Construct_2lzDmp63Mfw__oFMy0HdgWw(x, y, z, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


