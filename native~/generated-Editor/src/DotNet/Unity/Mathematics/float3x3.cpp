#include <DotNet/Unity/Mathematics/float3x3.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/Unity/Mathematics/float3.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct float3;
}
namespace DotNet::Unity::Mathematics {
struct float3x3;
}

namespace DotNet::Unity::Mathematics {

void (*float3x3::Construct_xZgBbnocutib2NGrHT9kpA)(const ::DotNet::Unity::Mathematics::float3* c0, const ::DotNet::Unity::Mathematics::float3* c1, const ::DotNet::Unity::Mathematics::float3* c2, ::DotNet::Unity::Mathematics::float3x3* pReturnValue, void** reinteropException) = nullptr;


float3x3 float3x3::Construct(const ::DotNet::Unity::Mathematics::float3& c0, const ::DotNet::Unity::Mathematics::float3& c1, const ::DotNet::Unity::Mathematics::float3& c2)
{
    void* reinteropException = nullptr;
    float3x3 result;
    Construct_xZgBbnocutib2NGrHT9kpA(&c0, &c1, &c2, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::Unity::Mathematics::float3x3::Property_get_Item)(const ::DotNet::Unity::Mathematics::float3x3* thiz, ::std::int32_t index, ::DotNet::Unity::Mathematics::float3* pReturnValue, void** reinteropException) = nullptr;


::DotNet::Unity::Mathematics::float3 float3x3::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    ::DotNet::Unity::Mathematics::float3 result;
    Property_get_Item(&(*this), index, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


