#include <DotNet/Unity/Mathematics/float4x4.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/Unity/Mathematics/float4.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct float4;
}
namespace DotNet::Unity::Mathematics {
struct float4x4;
}

namespace DotNet::Unity::Mathematics {

void (*float4x4::Construct_40mXKMXvvkbHdnVEuqJdsw)(const ::DotNet::Unity::Mathematics::float4* c0, const ::DotNet::Unity::Mathematics::float4* c1, const ::DotNet::Unity::Mathematics::float4* c2, const ::DotNet::Unity::Mathematics::float4* c3, ::DotNet::Unity::Mathematics::float4x4* pReturnValue, void** reinteropException) = nullptr;


float4x4 float4x4::Construct(const ::DotNet::Unity::Mathematics::float4& c0, const ::DotNet::Unity::Mathematics::float4& c1, const ::DotNet::Unity::Mathematics::float4& c2, const ::DotNet::Unity::Mathematics::float4& c3)
{
    void* reinteropException = nullptr;
    float4x4 result;
    Construct_40mXKMXvvkbHdnVEuqJdsw(&c0, &c1, &c2, &c3, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::Unity::Mathematics::float4x4::Property_get_Item)(const ::DotNet::Unity::Mathematics::float4x4* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::float4* pReturnValue, void** reinteropException) = nullptr;


::DotNet::Unity::Mathematics::float4 float4x4::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::float4 result;
    Property_get_Item(&(*this), index, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


