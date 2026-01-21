#include <DotNet/Unity/Mathematics/float3.h>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <cstdint>

namespace DotNet::Unity::Mathematics {
struct float3;
}

namespace DotNet::Unity::Mathematics {

void (*float3::Construct_LB__scTJntm1swre2IwXuIw)(float x, float y, float z, ::DotNet::Unity::Mathematics::float3* pReturnValue, void** reinteropException) = nullptr;


float3 float3::Construct(float x, float y, float z)
{
    void* reinteropException = nullptr;
    float3 result;
    Construct_LB__scTJntm1swre2IwXuIw(x, y, z, &result, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


float (*DotNet::Unity::Mathematics::float3::Property_get_Item)(const ::DotNet::Unity::Mathematics::float3* thiz, ::std::int32_t index, void** reinteropException) = nullptr;


float float3::operator[](::std::int32_t index) const {
    void* reinteropException = nullptr;
    auto result = Property_get_Item(&(*this), index, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


} // namespace DotNet::Unity::Mathematics


